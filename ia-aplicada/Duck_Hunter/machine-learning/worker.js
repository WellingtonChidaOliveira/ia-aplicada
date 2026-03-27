importScripts("https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@latest");

const MODEL_PATH = `yolov5n_web_model/model.json`;
const LABELS_PATH = `yolov5n_web_model/labels.json`;
const MODEL_SIZE_SCREEN = 640;
const TRASH_HOLD = 0.5;
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
    const tensor = tf.browser.fromPixels(image);

    return tf.image
      .resizeBilinear(tensor, [MODEL_SIZE_SCREEN, MODEL_SIZE_SCREEN])
      .div(255)
      .expandDims(0);
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

function* predictionDuck({ boxes, scores, classes }, width, height) {
  for (let i = 0; i < scores.length; i++) {
    if (scores[i] < TRASH_HOLD) continue;

    const label = _labels[classes[i]];
    if (label !== "kite") continue;

    let [x1, y1, x2, y2] = boxes.slice(i * 4, (i + 1) * 4);
    x1 *= width;
    y1 *= height;
    x2 *= width;
    y2 *= height;

    const centerX = (x1 + x2) / 2;
    const centerY = (y1 + y2) / 2;

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
  const { width, height } = data.image;

  const interfaceResult = await runInterface(input);
  for (const prediction of predictionDuck(interfaceResult, width, height)) {
    postMessage({
      type: "prediction",
      ...prediction,
    });
  }
};

console.log("🧠 YOLOv5n Web Worker initialized");
