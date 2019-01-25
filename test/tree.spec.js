import "@babel/polyfill";
import { schema, resolvers } from "../src/tree";
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

it("test treeRoot query", async () => {
  const TREEROOT_QUERY = gql`
    query {
      treeRoot {
        id
        parent
        index
        maxIndex
        maxHeight
        children {
          id
          index
          maxIndex
          maxHeight
        }
      }
    }
  `;

  const res = await query({
    query: TREEROOT_QUERY,
    variables: { analysis: ANALYSIS_ID }
  });
  expect(res).toMatchSnapshot();
});

it("test treeNode query with ID", async () => {
  const TREEROOT_QUERY = gql`
    query {
      treeNode {
        id
        parent
        index
        maxIndex
        maxHeight
        children {
          id
          index
          maxIndex
          maxHeight
        }
      }
    }
  `;

  const res = await query({
    query: TREEROOT_QUERY,
    variables: { analysis: ANALYSIS_ID, id: ["LOCI1"] }
  });
  expect(res).toMatchSnapshot();
});

it("test treeNode query with index", async () => {
  const TREEROOT_QUERY = gql`
    query {
      treeNode {
        id
        parent
        index
        maxIndex
        maxHeight
        children {
          id
          index
          maxIndex
          maxHeight
        }
      }
    }
  `;

  const res = await query({
    query: TREEROOT_QUERY,
    variables: { analysis: ANALYSIS_ID, index: 1 }
  });
  expect(res).toMatchSnapshot();
});

it("test treeNodes query", async () => {
  const TREEROOT_QUERY = gql`
    query {
      treeNodes {
        id
        parent
        index
        maxIndex
        maxHeight
        children {
          id
          index
          maxIndex
          maxHeight
        }
      }
    }
  `;

  const res = await query({
    query: TREEROOT_QUERY,
    variables: { analysis: ANALYSIS_ID, range: [0, 2] }
  });
  expect(res).toMatchSnapshot();
});
