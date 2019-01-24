import { schema, resolvers } from "../src/analysis";
import { startServer, stopServer } from "./test-server";
import { gql } from "apollo-server";

const util = require("util");

let query;
beforeAll(async () => {
  const client = await startServer(schema, resolvers);
  query = client.query;
});

it("has server started", () => {
  expect(query).toBeDefined();
});

it("test analysis", async () => {
  const DASHBOARD_QUERY = gql`
    query {
      dashboards {
        id
        analyses {
          id
          title
          description
          segsIndex
          treeIndex
        }
      }
    }
  `;

  const res = await query({ query: DASHBOARD_QUERY });

  console.log(util.inspect(res.data, { showHidden: false, depth: null }));
  expect(res).toBeDefined();
});
