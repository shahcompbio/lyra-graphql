import * as tree from "./tree.js";
import * as segs from "./segs.js";
import { merge } from "lodash";

import client from "./api/elasticsearch.js";

const { ApolloServer, gql } = require("apollo-server");

const schema = gql`
  type Query {
    dashboards: [Dashboard!]!
    analysis(analysis: String!, dashboard: String!): Analysis
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
`;

const allAnalysisQuery = () => ({
  size: 50000
});

const resolvers = {
  Query: {
    async dashboards() {
      const results = await client.search({
        index: "analysis",
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
        index: "analysis",
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
  }
};

const server = new ApolloServer({
  typeDefs: [schema, tree.schema, segs.schema],
  resolvers: merge(resolvers, tree.resolvers, segs.resolvers)
});

server.listen().then(({ url }) => console.log(`Server is running on ${url}`));
