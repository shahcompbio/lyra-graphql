const { gql } = require("apollo-server");

import client from "./api/elasticsearch.js";

export const schema = gql`
  extend type Query {
    hasPloidy(analysis: String!): Boolean
  }
`;

export const resolvers = {
  Query: {
    async hasPloidy(_, { analysis }) {
      const results = await client.indices.exists({
        index: `ce00_${analysis.toLowerCase()}_qc`
      });

      return results;
    }
  }
};
