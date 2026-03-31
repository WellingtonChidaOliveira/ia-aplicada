import "https://cdn.jsdelivr.net/npm/@tensorflow/tfjs@4.22.0/dist/tf.min.js";
import { workerEvents } from "/src/events/constants.js";

console.log("Model training worker initialized");
let _globalCtx = {};
let _model = null;

const WEIGHTS = {
  category: 0.4,
  color: 0.3,
  price: 0.2,
  age: 0.1,
};

const normalizeRange = (value, min, max) => (value - min) / (max - min || 1);

function makeContext(users, prodcuts) {
  const age = users.map((u) => u.age);
  const price = prodcuts.map((p) => p.price);

  const minAge = Math.min(...age);
  const maxAge = Math.max(...age);

  const minPrice = Math.min(...price);
  const maxPrice = Math.max(...price);

  const colors = [...new Set(prodcuts.map((p) => p.color))];
  const categories = [...new Set(prodcuts.map((p) => p.category))];

  const colorToIndex = Object.fromEntries(
    colors.map((color, index) => {
      return [color, index];
    }),
  );

  const categoryToIndex = Object.fromEntries(
    categories.map((category, index) => {
      return [category, index];
    }),
  );

  //mid age
  const midAge = (minAge + maxAge) / 2;
  //mid price
  const midPrice = (minPrice + maxPrice) / 2;
  const ageSum = {};
  const ageCount = {};
  users.forEach((user) => {
    user.purchases.forEach((purchase) => {
      ageSum[purchase.name] = (ageSum[purchase.name] || 0) + user.age;
      ageCount[purchase.name] = (ageCount[purchase.name] || 0) + 1;
    });
  });

  const productAvgAgeNormalized = Object.fromEntries(
    prodcuts.map((product) => {
      const avgAge = ageCount[product.name]
        ? ageSum[product.name] / ageCount[product.name]
        : midAge;

      return [product.name, normalizeRange(avgAge, minAge, maxAge)];
    }),
  );

  return {
    prodcuts,
    users,
    colorToIndex,
    categoryToIndex,
    productAvgAgeNormalized,
    minAge,
    maxAge,
    minPrice,
    maxPrice,
    midPriceNormalized: normalizeRange(midPrice, minPrice, maxPrice),
    numCategories: categories.length,
    numColors: colors.length,
    dimentision: 2 + categories.length + colors.length, //age, price, category one-hot, color one-hot
  };
}

//one hot take
const oneHotWeight = (index, length, weight) =>
  tf.oneHot(index, length).cast("float32").mul(weight);

function encodeProduct(product, ctx) {
  const price = tf.tensor1d([
    normalizeRange(product.price, ctx.minPrice, ctx.maxPrice) * WEIGHTS.price,
  ]);

  const age = tf.tensor1d([
    ctx.productAvgAgeNormalized[product.name] ?? 0.5 * WEIGHTS.age,
  ]);

  const category = oneHotWeight(
    ctx.categoryToIndex[product.category],
    ctx.numCategories,
    WEIGHTS.category,
  );

  const color = oneHotWeight(
    ctx.colorToIndex[product.color],
    ctx.numColors,
    WEIGHTS.color,
  );

  return tf.concat1d([price, age, category, color]);
}

function encodeUser(user, ctx) {
  if (user.purchases.length) {
    return tf
      .stack(
        user.purchases.map(
          (product) => (product = encodeProduct(product, ctx)),
        ),
      )
      .mean(0)
      .reshape([1, ctx.dimentision]);
  }

  return tf
    .concat1d([
      tf.zeros([1]),
      tf.tensor1d([
        normalizeRange(user.age, ctx.minAge, ctx.maxAge) * WEIGHTS.age,
      ]),
      tf.zeros([ctx.numCategories]),
      tf.zeros([ctx.numColors]),
    ])
    .reshape([1, ctx.dimentision]);
}

function createTrainingData(ctx) {
  let inputs = [];
  let labels = [];
  ctx.users
    .filter((u) => u.purchases.length)
    .forEach((user) => {
      const userVector = encodeUser(user, ctx).dataSync();
      ctx.prodcuts.forEach((product) => {
        const productVector = encodeProduct(product, ctx).dataSync();
        const label = user.purchases.some((p) => p.name === product.name)
          ? 1
          : 0;

        inputs.push([...userVector, ...productVector]);
        labels.push(label);
      });
    });

  return {
    xs: tf.tensor2d(inputs),
    ys: tf.tensor2d(labels, [labels.length, 1]),
    inputDimentions: ctx.dimentision * 2, //length of user vector + product vector
  };
}

async function congfigureNeuralNetAndTrain(trainData) {
  const model = tf.sequential();
  model.add(
    tf.layers.dense({
      inputShape: [trainData.inputDimentions],
      units: 128,
      activation: "relu",
    }),
  );
  model.add(tf.layers.dense({ units: 64, activation: "relu" }));
  model.add(tf.layers.dense({ units: 32, activation: "relu" }));

  model.add(tf.layers.dense({ units: 1, activation: "sigmoid" })); //compress to 0-1 for binary classification

  model.compile({
    optimizer: tf.train.adam(0.1),
    loss: "binaryCrossentropy",
    metrics: ["accuracy"],
  });

  await model.fit(trainData.xs, trainData.ys, {
    epochs: 100,
    batchSize: 32,
    shuffle: true,
    callbacks: {
      onEpochEnd: (epoch, logs) => {
        postMessage({
          type: workerEvents.trainingLog,
          epoch,
          loss: logs.loss,
          accuracy: logs.acc,
        });
      },
    },
  });

  return model;
}
async function trainModel({ users }) {
  console.log("Training model with users:", users);

  postMessage({
    type: workerEvents.progressUpdate,
    progress: { progress: 50 },
  });
  const prodcuts = await fetch("/data/products.json").then((res) => res.json());
  const ctx = makeContext(users, prodcuts);
  ctx.productVectors = prodcuts.map((product) => {
    return {
      name: product.name,
      meta: { ...product },
      vector: encodeProduct(product, ctx).dataSync(),
    };
  });

  _globalCtx = ctx;

  const trainData = createTrainingData(ctx);
  _model = await congfigureNeuralNetAndTrain(trainData);

  postMessage({
    type: workerEvents.progressUpdate,
    progress: { progress: 100 },
  });

  postMessage({
    type: workerEvents.trainingComplete,
  });
}
function recommend(user) {
  if (!_model) return;
  const ctx = _globalCtx;
  const userVector = encodeUser(user, ctx).dataSync();
  const inputs = ctx.productVectors.map(({ vector }) => {
    return [...userVector, ...vector];
  });

  const inputTensor = tf.tensor2d(inputs);
  const predictions = _model.predict(inputTensor);
  const scores = predictions.dataSync();
  const recommendations = ctx.productVectors
    .map((product, index) => {
      return {
        ...product.meta,
        name: product.name,
        score: scores[index],
      };
    })
    .sort((a, b) => b.score - a.score)
    .slice(0, 5);
  console.log("will recommend for user:", user);
  postMessage({
    type: workerEvents.recommend,
    user,
    recommendations: recommendations,
  });
}

const handlers = {
  [workerEvents.trainModel]: trainModel,
  [workerEvents.recommend]: (d) => recommend(d.user, _globalCtx),
};

self.onmessage = (e) => {
  const { action, ...data } = e.data;
  if (handlers[action]) handlers[action](data);
};
