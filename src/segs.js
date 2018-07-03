const { gql } = require("apollo-server");

import client from "./api/elasticsearch.js";

export const schema = gql`
  extend type Query {
    chromosomes(analysis: String!): [Chromosome]
    segs(analysis: String!, indices: [Int!]!): [SegRow]
    cloneSegs(analysis: String!, range: [Int!]!): [Seg]
  }

  type Chromosome {
    id: String!
    start: Int!
    end: Int!
  }

  type SegRow {
    id: String!
    index: Int!
    ploidy: Int!
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

async function getIDsForIndices(analysis, indices) {
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

  return results;
}

async function getIDsForRange(analysis, range) {
  const results = await client.search({
    index: `ce00_${analysis.toLowerCase()}_tree`,
    body: {
      size: 50000,
      query: {
        bool: {
          must: [
            {
              range: {
                heatmap_order: {
                  gte: range[0],
                  lte: range[1]
                }
              }
            }
          ]
        }
      }
    }
  });
  return results;
}

const getBinQuery = ids => {
  const rangeQuery = Array.apply(null, { length: 500 }).map(
    (_, i) => ({
      from: i === 0 ? 0 : 500000 * i + 1,
      to: (i + 1) * 500000
    }),
    []
  );

  return {
    size: 0,
    query: {
      bool: {
        must: [
          {
            terms: {
              cell_id: ids
            }
          }
        ]
      }
    },
    aggs: {
      chromosomes: {
        terms: {
          field: "chrom_number",
          size: 50
        },
        aggs: {
          bins: {
            histogram: {
              field: "start",
              interval: 500000
            },
            aggs: {
              state: {
                terms: {
                  field: "state",
                  size: 1
                }
              }
            }
          }
        }
      }
    }
  };
};

const getSegsForChromosome = (id, bins) => {
  const convertBinsToSegs = (currSeg, allSegs, bins) => {
    if (bins.length === 0) {
      return [...allSegs, currSeg];
    } else {
      const [firstBin, ...restBin] = bins;

      if (hasSameState(currSeg, firstBin)) {
        return convertBinsToSegs(
          mergeSegs(currSeg, firstBin),
          allSegs,
          restBin
        );
      } else {
        return convertBinsToSegs(
          convertToSeg(firstBin),
          [...allSegs, currSeg],
          restBin
        );
      }
    }
  };

  const getBinState = bin => bin.state.buckets[0].key;

  const hasSameState = (seg, bin) => seg.state === getBinState(bin);

  const mergeSegs = (seg, bin) => ({
    ...seg,
    end: bin.key + 500000
  });

  const convertToSeg = bin => ({
    chrom_number: id,
    start: bin.key === 0 ? bin.key : bin.key + 1,
    end: bin.key + 500000,
    state: getBinState(bin)
  });
  const [firstBin, ...restBin] = bins;
  return convertBinsToSegs(convertToSeg(firstBin), [], restBin);
};
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
      const results = await getIDsForIndices(analysis, indices);

      return results.hits.hits;
    },

    async cloneSegs(_, { analysis, range }) {
      const idResults = await getIDsForRange(analysis, range);
      const ids = idResults.hits.hits.map(record => record["_source"].cell_id);

      const cloneBins = await client.search({
        index: `cl00_${analysis.toLowerCase()}_bins`,
        body: getBinQuery(ids)
      });

      const results = cloneBins.aggregations.chromosomes.buckets.reduce(
        (results, chromosome) => [
          ...results,
          ...getSegsForChromosome(chromosome.key, chromosome.bins.buckets)
        ],
        []
      );

      const roundedResults = results.map(result => ({
        ...result,
        state: Math.round(result.state)
      }));
      return results;
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
    ploidy: async root => {
      const ploidyIndex = root["_index"].replace("_tree", "_qc");

      const isIndexExist = await client.indices.exists({
        index: ploidyIndex
      });

      if (isIndexExist) {
        const results = await client.search({
          index: ploidyIndex,
          body: {
            size: 50000,
            query: {
              bool: {
                filter: [{ term: { cell_id: root["_source"].cell_id } }]
              }
            }
          }
        });

        const hit = results.hits.hits;
        return hit.length === 0 ? -1 : hit[0]["_source"]["state_mode"];
      }
      return -1;
    },
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
