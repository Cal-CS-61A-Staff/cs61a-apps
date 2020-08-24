import React from "react";
import ReactDOM from "react-dom";
import "./index.css";
import StudentView from "./App";
import * as serviceWorker from "./serviceWorker";

ReactDOM.render(<StudentView />, document.getElementById("root"));

if (module.hot) {
    module.hot.accept("./App", () => {
        const NextApp = require("./App").StudentView;
        ReactDOM.render(
            <NextApp />,
            document.getElementById("root"),
        );
    });
}


// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();
