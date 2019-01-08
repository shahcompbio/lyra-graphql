import { schema, resolvers } from "../src/analysis";
import { startServer, stopServer } from "./test-server";
import { graphql } from "graphql";

let server;
beforeAll(async () => {
  server = await startServer(schema);
});

afterAll(() => {
  stopServer(server);
});

test("has server started", () => {
  expect(server).toBeDefined();
});
