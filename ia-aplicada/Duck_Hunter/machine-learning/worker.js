importScripts("https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@latest");

const MODEL_PATH = `yolov5n_web_model/model.json`;
const LABELS_PATH = `yolov5n_web_model/labels.json`;
const MODEL_SIZE_SCREEN = 640;
const TRASH_HOLD = 0.3;
let _labels = [];
let _model = null;
//load models and image
async function loadModelAndLabels() {
  await tf.ready();

  _labels = await fetch(LABELS_PATH).then((res) => res.json());
  _model = await tf.loadGraphModel(MODEL_PATH);

  //dummy train
  const dummyInput = tf.ones(_model.inputs[0].shape);
  await _model.executeAsync(dummyInput);
  tf.dispose(dummyInput);

  postMessage({ type: "model_loaded" });
}

function preprocessImage(image) {
  return tf.tidy(() => {
    let tensor = tf.browser.fromPixels(image);

    const height = image.height;
    const width = image.width;

    // Scale preserving aspect ratio to fit inside [640, 640]
    const scale = MODEL_SIZE_SCREEN / Math.max(height, width);
    const newHeight = Math.round(height * scale);
    const newWidth = Math.round(width * scale);

    tensor = tf.image.resizeBilinear(tensor, [newHeight, newWidth]);

    // Pad bottom and right to make it exactly 640x640
    const padHeight = MODEL_SIZE_SCREEN - newHeight;
    const padWidth = MODEL_SIZE_SCREEN - newWidth;

    tensor = tf.pad(tensor, [
      [0, padHeight],
      [0, padWidth],
      [0, 0],
    ]);

    return tensor.div(255).expandDims(0);
  });
}

async function runInterface(input) {
  const output = await _model.executeAsync(input);
  tf.dispose(input);
  const [boxes, scores, classes] = output.slice(0, 3);
  const [boxesData, scoresData, classesData] = await Promise.all([
    boxes.data(),
    scores.data(),
    classes.data(),
  ]);

  output.forEach((tensor) => tf.dispose(tensor));

  return { boxes: boxesData, scores: scoresData, classes: classesData };
}

function* predictionDuck(
  { boxes, scores, classes },
  imageWidth,
  imageHeight,
  stageWidth,
  stageHeight,
) {
  // L is the dimension that was scaled exactly to 640
  const L = Math.max(imageWidth, imageHeight);

  for (let i = 0; i < scores.length; i++) {
    if (scores[i] < TRASH_HOLD) continue;

    const label = _labels[classes[i]];
    if (label !== "kite") continue;

    let [x1, y1, x2, y2] = boxes.slice(i * 4, (i + 1) * 4);

    // 1. Map normalized coords (0-1 against 640x640) back to the pixel coords of the extracted image space
    x1 *= L;
    y1 *= L;
    x2 *= L;
    y2 *= L;

    // 2. Center of bounding box in image pixel space
    const centerImgX = (x1 + x2) / 2;
    const centerImgY = (y1 + y2) / 2;

    // 3. Map pixel coords of the extracted image to the logical stage coordinate space
    const centerX = centerImgX * (stageWidth / imageWidth);
    const centerY = centerImgY * (stageHeight / imageHeight);

    yield {
      x: centerX,
      y: centerY,
      score: (scores[i] * 100).toFixed(2),
      timestamp: performance.now(),
    };
  }
}

loadModelAndLabels();
self.onmessage = async ({ data }) => {
  if (data.type !== "predict") return;

  if (!_model) return;

  const input = preprocessImage(data.image);

  const imageWidth = data.image.width;
  const imageHeight = data.image.height;
  const stageWidth = data.stageWidth || 800;
  const stageHeight = data.stageHeight || 600;

  const interfaceResult = await runInterface(input);
  for (const prediction of predictionDuck(
    interfaceResult,
    imageWidth,
    imageHeight,
    stageWidth,
    stageHeight,
  )) {
    postMessage({
      type: "prediction",
      ...prediction,
    });
  }
};

console.log("🧠 YOLOv5n Web Worker initialized");
