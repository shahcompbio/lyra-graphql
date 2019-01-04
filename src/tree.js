const { gql } = require("apollo-server");

import client from "./api/elasticsearch.js";

export const schema = gql`
  extend type Query {
    treeRoot(analysis: String!): Node
    treeNode(analysis: String!, id: String, index: Int): Node
    treeNodes(analysis: String!, range: [Int!]!): [Node]
  }

  type Node {
    id: [String]!
    parent: String!
    index: Int!
    maxIndex: Int!
    maxHeight: Int!
    children: [NodeChild!]!
  }

  type NodeChild {
    id: String!
    index: Int!
    maxIndex: Int!
    maxHeight: Int!
  }
`;

export const resolvers = {
  Query: {
    async treeRoot(_, { analysis }) {
      const results = await client.search({
        index: `ce00_${analysis.toLowerCase()}_tree`,
        body: {
          size: 1,
          query: {
            bool: {
              filter: [{ term: { parent: "root" } }]
            }
          }
        }
      });

      return results.hits.hits[0];
    },

    async treeNode(_, { analysis, id, index }) {
      const term = id ? { cell_id: id } : { heatmap_order: index };

      const results = await client.search({
        index: `ce00_${analysis.toLowerCase()}_tree`,
        body: {
          size: 1,
          query: {
            bool: {
              filter: [{ term: term }]
            }
          }
        }
      });
      return results.hits.hits[0];
    },

    async treeNodes(_, { analysis, range }) {
      const [minIndex, maxIndex] = range;

      const results = await client.search({
        index: `ce00_${analysis.toLowerCase()}_tree`,
        body: {
          size: 50000,
          sort: [
            {
              heatmap_order: {
                order: "asc"
              }
            }
          ],
          query: {
            bool: {
              must: [
                {
                  range: {
                    heatmap_order: {
                      gte: minIndex,
                      lte: maxIndex
                    }
                  }
                }
              ]
            }
          }
        }
      });

      return results.hits.hits;
    }
  },
  Node: {
    id: root => root["_source"].cell_id.split(",").map(item => item.trim()),
    parent: root => root["_source"].parent,
    index: root => root["_source"].heatmap_order,
    maxIndex: root => root["_source"].max_index,
    maxHeight: root => root["_source"].max_height,
    children: root => {
      return root["_source"].children.map(async child => {
        const results = await client.search({
          index: root["_index"],
          body: {
            size: 1,
            query: {
              bool: {
                filter: [{ term: { unmerged_id: child } }]
              }
            }
          }
        });
        return results.hits.hits[0]["_source"];
      });
    }
  },

  NodeChild: {
    id: root => root.cell_id,
    index: root => root.heatmap_order,
    maxIndex: root => root.max_index,
    maxHeight: root => root.max_height
  }
};
