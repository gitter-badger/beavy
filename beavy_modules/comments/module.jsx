import React from "react";
import { Link } from "react-router";
import {registerMainMenuItem} from '../../jsbeavy/app/components/MainMenu.jsx';

console.log(registerMainMenuItem)

registerMainMenuItem(function() {
  return (<li><Link to="home">other</Link> this comes from comments</li>)
});