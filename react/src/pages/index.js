import React, { Component } from "react";
import styled from "styled-components";
import * as polished from "polished";

import LiveEdit from "../components/LiveEdit";

const Container = styled.div`
  margin: 0 auto;
  max-width: 100%;
  width: ${polished.rem(1440)};
  padding: ${polished.rem(20)};
  padding-bottom: ${polished.rem(100)};
  text-align: center;
`;

const componentClassExample = `
class WebPage extends React.Component {
  constructor() {
    super();
    this.state = {
      total: 0,
    };
  }
  
  render() {
    let handleClick = () => {
      this.setState({
        total: this.state.total + 1,
      });
    };
    let buttonList = [];
    for (let i = 0; i != 3; ++i) {
      buttonList.push(
        <Button onClick={handleClick} />
      );
    }
    return (
      <div>
        <Header
          text={this.state.total + " total clicks!"}
        />
        <Body text="Some body text!" />
        {buttonList}
      </div>
    );
  }
}

class Header extends React.Component {
  render() {
    return (
      <h2>
        {this.props.text}
      </h2>
    );
  }
}

class Body extends React.Component {
  render() {
    return (
      <div>
        {this.props.text}
      </div>
    );
  }
}

class Button extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      numClicks: 0,
    };
  }
  
  render() {
    let handleClick = () => {
      this.setState({
        numClicks: this.state.numClicks + 1,
      });
      this.props.onClick();
    };
    return (
      <div>
        <button onClick={handleClick}>
          Clicked
          {" "}
          {this.state.numClicks}
          {" "}
          times!
        </button>
      </div>
    );
  }
}

render(WebPage);
`.trim();
`
() => (
  <h3>
    So functional. Much wow!
  </h3>
)
`.trim();
`
<h3>
  Hello World!
</h3>
`.trim();
`
const Wrapper = ({ children }) => (
  <div style={{
    background: 'papayawhip',
    width: '100%',
    padding: '2rem'
  }}>
    {children}
  </div>
)

const Title = () => (
  <h3 style={{ color: 'palevioletred' }}>
    Hello World!
  </h3>
)

render(
  <Wrapper>
    <Title />
  </Wrapper>
)
`.trim();

class Index extends Component {
  render() {
    return (
      <Container>
        <LiveEdit noInline code={componentClassExample} />
      </Container>
    );
  }
}

export default Index;
