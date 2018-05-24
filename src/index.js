const { GraphQLServer } = require("graphql-yoga");
const fetch = require("node-fetch");
const elasticsearch = require("elasticsearch");
const util = require("util");
let client = new elasticsearch.Client({
  host: "localhost:9200",
  log: "trace"
});

const typeDefs = `
type Query {
  dashboards: [Dashboard!]!
  analysis(analysis: String!, dashboard: String!): Analysis
  treeRoot(analysis: String!): Node
  treeNode(analysis: String!, cellID: String!): Node
}

type Dashboard {
  id: String!
  analyses: [Analysis!]!
}

type Analysis {
  id: String!
  title: String!
  description: String!
  segsIndex: String!
  treeIndex: String!
}

type Node {
  id: String!
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

const allAnalysisQuery = () => ({
  size: 50000
});

const resolvers = {
  Query: {
    async dashboards() {
      const results = await client.search({
        index: "tree_analysis",
        body: {
          size: 50000,
          aggs: {
            dashboards: {
              terms: {
                field: "dashboard",
                size: 50000
              }
            }
          }
        }
      });
      return results.aggregations.dashboards.buckets.map(bucket => ({
        id: bucket.key,
        analyses: results.hits.hits.map(hit => hit["_source"])
      }));
    },
    async analysis(_, { analysis, dashboard }) {
      const results = await client.search({
        index: "tree_analysis",
        body: {
          query: {
            bool: {
              must: [
                {
                  term: {
                    dashboard: {
                      value: dashboard
                    }
                  }
                },
                {
                  term: {
                    analysis_id: {
                      value: analysis
                    }
                  }
                }
              ]
            }
          }
        }
      });

      return results.hits.hits[0]["_source"];
    },

    async treeRoot(_, { analysis }) {
      const results = await client.search({
        index: analysis + "_tree",
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

    async treeNode(_, { analysis, cellID }) {
      const results = await client.search({
        index: analysis + "_tree",
        body: {
          size: 1,
          query: {
            bool: {
              filter: [{ term: { cell_id: cellID } }]
            }
          }
        }
      });
      return results.hits.hits[0];
    }
  },
  Dashboard: {
    id: root => root.id,
    analyses: root => {
      const dashboard = root.id;
      return root.analyses.filter(analysis => analysis.dashboard === dashboard);
    }
  },

  Analysis: {
    id: root => root.analysis_id,
    title: root => root.title,
    description: root => root.description,
    segsIndex: root => root.segs_index,
    treeIndex: root => root.tree_index
  },

  Node: {
    id: root => root["_source"].cell_id,
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
                filter: [{ term: { cell_id: child } }]
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

const server = new GraphQLServer({
  typeDefs,
  resolvers
});

server.start(() => console.log("Server is running on http://localhost:4000"));
