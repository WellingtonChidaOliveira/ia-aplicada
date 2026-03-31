import Fastify from "fastify";

const service = Fastify();

service.post("/chat", async  (request, reply) => {
    const { message } = request.body as { message: string };
    console.log(message);
});

try{
    await service.listen({ port: 3000 });
    console.log("Server running on port 3000");
}catch(error){
    console.error(error);
    process.exit(1);
}


service.inject({
    method: "POST",
    url: "/chat",
    payload: {
        message: "Hello"
    }
}).then((response) => {
    console.log(response);
});


    



    