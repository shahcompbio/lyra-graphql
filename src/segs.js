const { gql } = require("apollo-server");

import client from "./api/elasticsearch.js";

export const schema = gql`
  extend type Query {
    chromosomes(analysis: String!): [Chromosome]
    segs(analysis: String!, indices: [Int!]!): [SegRow]
  }

  type Chromosome {
    id: String!
    start: Int!
    end: Int!
  }

  type SegRow {
    id: String!
    index: Int!
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

export const resolvers = {
  Query: {
    async chromosomes(_, { analysis }) {
      const results = await client.search({
        index: `ce00_${analysis.toLowerCase()}_segs`,
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
