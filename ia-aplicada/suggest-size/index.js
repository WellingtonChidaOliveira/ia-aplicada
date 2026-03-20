import tf from '@tensorflow/tfjs';

async function trainModel(inputXs, outputYs) {
    const model = tf.sequential()

    model.add(tf.layers.dense({ inputShape: [5], units: 80, activation: 'relu' }))
    model.add(tf.layers.dense({ units: 4, activation: 'softmax' }))

    model.compile({
        optimizer: tf.train.adam(),
        loss: 'categoricalCrossentropy',
        metrics: ['accuracy']
    })

    await model.fit(inputXs, outputYs, {
        verbose: 0,
        epochs: 100,
        shuffle: true,
        callbacks: {
            onEpochEnd: (epoch, logs) => {
                console.log(`Epoch ${epoch + 1}: loss = ${logs.loss.toFixed(4)}, accuracy = ${logs.acc.toFixed(4)}`);
            }
        }
    })
    return model
}
async function predict(model, newData) {
    const tfInput = tf.tensor2d(newData);
    const pred =  model.predict(tfInput);
    const predArray = await pred.array();
    return predArray[0].map((value, index) => ({ size: clothesSize[index], probability: value }));
}
function normalizeRange(value, min, max) {
  return (value - min) / (max - min);
}

const personToTrainModel = [
    { name: 'Alice', height: 165, weight: 68, age: 30, gender: 'female'},
    { name: 'Mathues', height: 175, weight: 78, age: 25, gender: 'male'},
    { name: 'Bob', height: 180, weight: 85, age: 28, gender: 'male'},
    { name: 'Eve', height: 160, weight: 55, age: 22, gender: 'female'},
    { name: 'Charlie', height: 170, weight: 75, age: 35, gender: 'male'},
    { name: 'Diana', height: 155, weight: 50, age: 19, gender: 'female'},
    { name: 'Frank', height: 185, weight: 90, age: 40, gender: 'male'},
    { name: 'Grace', height: 168, weight: 62, age: 27, gender: 'female'},
    { name: 'Henry', height: 178, weight: 80, age: 32, gender: 'male'},
    { name: 'Ivy', height: 162, weight: 58, age: 24, gender: 'female'},
    { name: 'Jack', height: 172, weight: 72, age: 29, gender: 'male'},
    { name: 'Kate', height: 158, weight: 52, age: 21, gender: 'female'},
    { name: 'Liam', height: 182, weight: 88, age: 38, gender: 'male'},
    { name: 'Mia', height: 164, weight: 60, age: 26, gender: 'female'}
]

const ages = personToTrainModel.map(p => p.age);
const heights = personToTrainModel.map(p => p.height);
const weights = personToTrainModel.map(p => p.weight);

const minAge = Math.min(...ages);
const maxAge = Math.max(...ages);
const minHeight = Math.min(...heights);
const maxHeight = Math.max(...heights);
const minWeight = Math.min(...weights);
const maxWeight = Math.max(...weights);

const normalizedData = personToTrainModel.map(p => [
    parseFloat(normalizeRange(p.height, minHeight, maxHeight).toFixed(2)),
    parseFloat(normalizeRange(p.weight, minWeight, maxWeight).toFixed(2)),
    parseFloat(normalizeRange(p.age, minAge, maxAge).toFixed(2)),
    ...tf.oneHot(p.gender === 'male' ? 1 : 0, 2).arraySync()
]);

console.log(normalizedData);

const clothesSize = ["small", "medium", "large", "x-large"];
const normalizedSizes = personToTrainModel.map(p =>  {
    if (p.height < 160 || p.weight < 60) {
        return tf.oneHot(0, 4).arraySync();
    }else if (p.height < 170 || p.weight < 70) {
        return tf.oneHot(1, 4).arraySync();
    }else if (p.height < 180 || p.weight < 80) {
        return tf.oneHot(2, 4).arraySync();
    }else {
        return tf.oneHot(3, 4).arraySync();
    }
});


const inputXs = tf.tensor2d(normalizedData);
const outputYs = tf.tensor2d(normalizedSizes);

const model = await trainModel(inputXs, outputYs)

const testPerson = { name: 'Test', height: 165, weight: 50, age: 22, gender: 'female'};
const normalizedTestPerson = [
    [
        parseFloat(normalizeRange(testPerson.height, minHeight, maxHeight).toFixed(2)),
        parseFloat(normalizeRange(testPerson.weight, minWeight, maxWeight).toFixed(2)),
        parseFloat(normalizeRange(testPerson.age, minAge, maxAge).toFixed(2)),
        ...tf.oneHot(testPerson.gender === 'male' ? 1 : 0, 2).arraySync()
    ]
];


const predictions = await predict(model, normalizedTestPerson);
const results = predictions
.sort((a, b) => b.probability - a.probability)
.map(p => `${p.size}: ${(p.probability * 100).toFixed(2)}%`)
.join('\n')

console.log(`Predicted clothing size probabilities for ${testPerson.name}:\n${results}`);