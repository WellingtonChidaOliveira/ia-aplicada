import { buildLayout } from "./layout";

// Must match the logical stage dimensions in Stage.js
const STAGE_MAX_X = 800;
const STAGE_MAX_Y = 600;

export default async function main(game) {
    const container = buildLayout(game.app);
    const worker = new Worker(new URL('./worker.js', import.meta.url), { type: 'module' });

    game.stage.aim.visible = false;

    worker.onmessage = ({ data }) => {
        const { type, x, y } = data;

        if (type === 'prediction') {
            console.log(`🎯 AI predicted at: (${x}, ${y})`);
            container.updateHUD(data);
            game.stage.aim.visible = true;

            game.stage.aim.setPosition(data.x, data.y);
            const position = game.stage.aim.getGlobalPosition();

            game.handleClick({
                global: position,
            });

        }

    };

    setInterval(async () => {
        const canvas = game.app.renderer.extract.canvas(game.stage);
        const bitmap = await createImageBitmap(canvas);

        worker.postMessage({
            type: 'predict',
            image: bitmap,
            // Send the logical stage dimensions so the worker scales
            // predictions to the stage coordinate system, not the
            // screen pixel coordinate system.
            stageWidth: STAGE_MAX_X,
            stageHeight: STAGE_MAX_Y,
        }, [bitmap]);

    }, 200); // every 200ms

    return container;
}
