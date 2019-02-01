const { gql } = require("apollo-server");

import client from "./api/elasticsearch.js";

export const schema = gql`
  extend type Query {
    dashboards: [Dashboard!]!
    analyses: [Analysis!]!
    analysis(analysis: String!): Analysis
  }

  type Dashboard {
    id: String!
    analyses: [Analysis!]!
  }

  type Analysis {
    id: String!
    title: String!
    description: String!
  }
`;

export const resolvers = {
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
    async analyses() {
      const results = await client.search({
        index: "analysis",
        body: {
          size: 50000
        }
      });

      return results.hits.hits.map(hit => hit["_source"]);
    },

    async analysis(_, { analysis }) {
      const results = await client.search({
        index: "analysis",
        body: {
          query: {
            bool: {
              must: [
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
    description: root => root.description
  }
};
