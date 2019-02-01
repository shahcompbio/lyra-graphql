import "@babel/polyfill";
import { schema, resolvers } from "../src/analysis";
import { startServer, stopServer } from "./test-server";
import { gql } from "apollo-server";

let query;
beforeAll(async () => {
  const client = await startServer(schema, resolvers);
  query = client.query;
});

it("has server started", () => {
  expect(query).toBeDefined();
});

it("test dashboard query", async () => {
  const DASHBOARD_QUERY = gql`
    query {
      dashboards {
        id
        analyses {
          id
          title
          description
        }
      }
    }
  `;

  const res = await query({ query: DASHBOARD_QUERY });
  expect(res).toMatchSnapshot();
});

it("test analyses query", async () => {
  const ANALYSES_QUERY = gql`
    query {
      analyses {
        id
        title
        description
      }
    }
  `;

  const res = await query({ query: ANALYSES_QUERY });
  expect(res).toMatchSnapshot();
});

it("test analysis query", async () => {
  const ANALYSIS_QUERY = gql`
    query {
      analysis(analysis: "ABC_123") {
        id
        title
        description
      }
    }
  `;

  const res = await query({ query: ANALYSIS_QUERY });
  expect(res).toMatchSnapshot();
});
