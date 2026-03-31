import Fastify from "fastify";

export const createServer = () => {
    const service = Fastify();

    service.post("/chat",{
        schema:{
            body:{
                type: "object",
                required: ["question"],
                properties:{
                    question:{type: "string"},
                }
            }
        }
    },async (request, reply) => {
        try {
            const {question} = request.body as {question:string};
            const response = "teste";
            return reply.send(response)

        } catch (error) {
            console.log("Error handling /chat request:", error);
            return reply.status(500).send({error: "Internal server error"})
        }
    });

    return service;
}


        