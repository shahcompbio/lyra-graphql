import "babel-polyfill";

const { ApolloServer } = require("apollo-server-express");

const express = require("express");

export async function startServer(schema) {
  const server = await new ApolloServer({
    typeDefs: schema,
    mock: true
  });

  const app = express();
  await server.applyMiddleware({ app });
  return await app.listen({ port: 4000 }, () =>
    console.log(`🚀 Server ready at http://localhost:4000${server.graphqlPath}`)
  );
}

export const stopServer = server => {
  server.close();
};
