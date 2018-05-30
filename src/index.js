const { GraphQLServer } = require("graphql-yoga");
const { ApolloServer, gql } = require("apollo-server");
const fetch = require("node-fetch");
const elasticsearch = require("elasticsearch");
const util = require("util");
let client = new elasticsearch.Client({
  host: "localhost:9200"
});

const typeDefs = gql`
  type Query {
    dashboards: [Dashboard!]!
    analysis(analysis: String!, dashboard: String!): Analysis
    treeRoot(analysis: String!): Node
    treeNode(analysis: String!, id: String, index: Int): Node
    treeNodes(analysis: String!, range: [Int!]!): [Node]
    chromosomes(analysis: String!): [Chromosome]
    segs(analysis: String!, indices: [Int!]!): [SegRow]
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

  type Chromosome {
    id: String!
    start: Int!
    end: Int!
  }

  type SegRow {
    id: String!
    index: String!
    segs: [Seg!]!
  }

  type Seg {
    chromosome: String!
    start: Int!
    end: Int!
    state: Int!
    integerMedian: Float!
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
        index: analysis.toLowerCase() + "_tree",
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
        index: analysis.toLowerCase() + "_tree",
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
        index: analysis.toLowerCase() + "_tree",
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
    },

    async chromosomes(_, { analysis }) {
      const results = await client.search({
        index: analysis.toLowerCase() + "_segs",
        body: {
          size: 0,
          aggs: {
            chrom_ranges: {
              terms: {
                field: "chrom_number",
                size: 50000,
                order: {
                  _key: "asc"
                }
              },
              aggs: {
                XMax: {
                  max: {
                    field: "end"
                  }
                },
                XMin: {
                  min: {
                    field: "start"
                  }
                }
              }
            }
          }
        }
      });

      return results.aggregations.chrom_ranges.buckets;
    },

    async segs(_, { analysis, indices }) {
      const results = await client.search({
        index: analysis.toLowerCase() + "_tree",
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
                  terms: {
                    heatmap_order: indices
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
  },

  Chromosome: {
    id: root => root.key,
    start: root => root.XMin.value,
    end: root => root.XMax.value
  },

  SegRow: {
    id: root => root["_source"].cell_id,
    index: root => root["_source"].heatmap_order,
    segs: async root => {
      const results = await client.search({
        index: root["_index"].replace("_tree", "_segs"),
        body: {
          size: 50000,
          query: {
            bool: {
              filter: [{ term: { cell_id: root["_source"].cell_id } }]
            }
          }
        }
      });

      return results.hits.hits.map(seg => seg["_source"]);
    }
  },

  Seg: {
    chromosome: root => root.chrom_number,
    start: root => root.start,
    end: root => root.end,
    state: root => root.state,
    integerMedian: root => root.integer_median
  }
};

const server = new ApolloServer({
  typeDefs,
  resolvers
});

server.listen().then(({ url }) => console.log(`Server is running on ${url}`));
