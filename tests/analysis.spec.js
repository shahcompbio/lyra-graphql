import { schema, resolvers } from "../src/analysis";
import { startServer, stopServer } from "./test-server";
import { graphql } from "graphql";

it("should start and close server", async () => {
  const server = await startServer(schema);
  expect(server).toBeDefined();
  stopServer(server);
});
