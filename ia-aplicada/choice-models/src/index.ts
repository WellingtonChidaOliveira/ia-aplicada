import { createServer } from "./server.ts";


const service = createServer();

service.inject({
    method: "POST",
    url: "/chat",
    payload: {
        question: "Hello"
    }
}).then((response) => {
    console.log("resp:",response.body);
});


    



    