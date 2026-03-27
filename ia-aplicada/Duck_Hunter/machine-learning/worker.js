importScripts("https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@latest");

const MODEL_PATH = `yolov5n_web_model/model.json`;
const LABELS_PATH = `yolov5n_web_model/labels.json`;
const MODEL_INPUT_SIZE = 640;

/*
 steps to construct predict game

 first - load model and labels(fetch labels)
 second - load model (using model_path/ YOLO)
 third - warm up model
 fourth -  execute model using dummy and dispose tensor
 fifth - post message model-load
 sixth - transforme image to tensor when predict is called
 seventh - setting dimension 640 x 640
 eighth - process image with resizeBilinear with div 255 to transform to tensor 0 -1
 ninth - get data model run interface
 tenth - execute model and dispose tensor
 eleventh - transforme in js object with (x, y), score and class (boxes, scores, class)
 twelfth - filter by score > 0.5
 thirteenth -   dispose objects
 fourteenth -  return object with (x, y), score and class
 
 */

let _labels = [];
let _model = null;

//first step
//load labels and models
//warmup the model
//post message model-loaded
async function loadModelAndLabels() {
  await tf.ready();

  _labels = await fetch(LABELS_PATH).then((res) => res.json());
  _model = await tf.loadGraphModel(MODEL_PATH);

  //warmup
  const dummy = tf.ones(_model.inputs[1].shape);
  await _model.executeAsync(dummy);

  postMessage({ type: "model-loaded" });
}

function processImage(image) {
  //dispose all tensors
  return tf.tidy(() => {
    //transform image to tensor
    const imageTensor = tf.browser.fromPixels(image);

    //setting dimension 640 x 640
    //div 255 to transform to tensor 0 -1
    //expand dimension to 1
    //return tensor
    return tf.image
      .resizeBilinear(imageTensor, [MODEL_INPUT_SIZE, MODEL_INPUT_SIZE])
      .div(255)
      .expandDims(0);
  });
}

//Execute model pass tensor image
//get boxes, scores and classes propies from image
//dispose tensor
//return object with boxes, scores and classes
async function runInterfaces(tensor) {
  const output = await _model.executeAsync(tensor);
  tf.dispose(tensor);

  const [boxes, scores, classes] = output.slice(0, 3);
  const [boxesData, scoresData, classesData] = await Promise.all([
    boxes.data(),
    scores.data(),
    classes.data(),
  ]);

  output.forEach((t) => t.dispose());

  return {
    boxesData,
    scoresData,
    classesData,
  };
}

loadModelAndLabels();
//after load models and labels verify if model is loaded correctly
//process image

self.onmessage = async ({ data }) => {
  if (data.type !== "predict") return;

  if (!_model) return;
  const input = processImage(data.image);
  const { width, height } = data.image;

  const interfaceResults = await runInterfaces(input);

  postMessage({
    type: "prediction",
    x: 400,
    y: 400,
    score: 0,
  });
};

console.log("🧠 YOLOv5n Web Worker initialized");
