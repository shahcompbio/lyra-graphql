const { GraphQLServer } = require("graphql-yoga");
const fetch = require("node-fetch");
const elasticsearch = require("elasticsearch");

let client = new elasticsearch.Client({
  host: "localhost:9200",
  log: "trace"
});

const typeDefs = `
type Query {
  dashboards: [Dashboard!]!
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

const server = new GraphQLServer({
  typeDefs,
  resolvers
});

server.start(() => console.log("Server is running on http://localhost:4000"));
