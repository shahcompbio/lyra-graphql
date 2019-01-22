import "babel-polyfill";

const { ApolloServer } = require("apollo-server");
const { createTestClient } = require("apollo-server-testing");
const { MockList } = require("apollo-server");

const mocks = {
  Query: () => ({
    dashboards: () => new MockList([1, 3])
  })
};

export async function startServer(schema) {
  const server = await new ApolloServer({
    typeDefs: schema,
    mocks
  });

  return createTestClient(server);
}
