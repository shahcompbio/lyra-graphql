import "@babel/polyfill";
import { schema, resolvers } from "../src/segs";
import { startServer, stopServer } from "./test-server";
import { gql } from "apollo-server";

const ANALYSIS_ID = "ABC_123";

let query;
beforeAll(async () => {
  const client = await startServer(schema, resolvers);
  query = client.query;
});

it("has server started", () => {
  expect(query).toBeDefined();
});

it("test chromosomes query", async () => {
  const CHROMOSOMES_QUERY = gql`
    query {
      chromosomes {
        id
        start
        end
      }
    }
  `;

  const res = await query({
    query: CHROMOSOMES_QUERY,
    variables: { analysis: ANALYSIS_ID }
  });
  expect(res).toMatchSnapshot();
});

it("test segs query", async () => {
  const SEGS_QUERY = gql`
    query {
      segs {
        id
        name
        index
        ploidy
        segs {
          chromosome
          start
          end
          state
        }
      }
    }
  `;

  const res = await query({
    query: SEGS_QUERY,
    variables: { analysis: ANALYSIS_ID, indices: [0, 2] }
  });
  expect(res).toMatchSnapshot();
});
