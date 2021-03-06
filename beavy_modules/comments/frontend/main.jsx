import React from "react";
import { Link, Route } from "react-router";
import { addExtension } from 'config/extensions';
import { make_url } from 'utils';

import { loadComments } from './actions';
import CommentsView from './views/Comments';
import CommentView from './views/Comment';

// addExtension("MainMenuItem", function() {
//   return (<li><Link to="home">other</Link> this comes from comments</li>)
// });

addExtension("userNavigationItems", (function() {
    return <Link to={make_url.account("comments/")}>My Comments</Link>;
  }));
addExtension("accountRoutes",
  <Route path="comments/" component={CommentsView} /> );
addExtension("accountRoutes",
  <Route path="comments/:commentId/" component={CommentView} /> );


