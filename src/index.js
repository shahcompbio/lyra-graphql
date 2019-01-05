import "babel-polyfill";
import * as tree from "./tree.js";
import * as segs from "./segs.js";
import * as metrics from "./metrics.js";
import * as analysis from "./analysis.js";
import { merge } from "lodash";

const { ApolloServer } = require("apollo-server");

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
const { registerServer } = require("apollo-server-express");
const app = express();
registerServer({ server, app, path: "/graphql" });

server.listen().then(({ url }) => console.log(`Server is running on ${url}`));
