import "babel-polyfill";
import * as tree from "./tree.js";
import * as segs from "./segs.js";
import * as metrics from "./metrics.js";
import * as analysis from "./analysis.js";
import { merge } from "lodash";

const { ApolloServer } = require("apollo-server-express");

const server = new ApolloServer({
  typeDefs: [analysis.schema, tree.schema, segs.schema, metrics.schema],
  resolvers: merge(
    analysis.resolvers,
    tree.resolvers,
    segs.resolvers,
    metrics.resolvers
  )
});

const express = require("express");
const app = express();
server.applyMiddleware({ app });

app.listen({ port: 4000 }, () =>
  console.log(`🚀 Server ready at http://localhost:4000${server.graphqlPath}`)
);
