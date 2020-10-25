import React, {
  useCallback,
  useContext,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { Form, FormControl, InputGroup } from "react-bootstrap";
import Anchor from "./Anchor";
import { getToken } from "./auth";
import debounce from "./debounce";
import ExamContext from "./ExamContext";
import FailText from "./FailText";
import LoadingButton from "./LoadingButton";
import Points from "./Points";
import post from "./post";

export default function Question({ question, number }) {
  const examContext = useContext(ExamContext);

  const defaultValue = examContext.savedAnswers[question.id] || "";

  const [value, actuallySetValue] = useState(defaultValue);
  const [savedValue, setSavedValue] = useState(defaultValue);
  const [saving, setSaving] = useState(false);
  const [failText, setFailText] = useState("");

  const setValue = (val) => {
    if (!examContext.locked) {
      actuallySetValue(val);
      if (val[0]) {
        examContext.recordSolved(question.id);
      } else {
        examContext.recordUnsolved(question.id);
      }
    }
  };

  useEffect(() => {
    if (defaultValue[0]) {
      examContext.recordSolved(question.id);
    } else {
      examContext.recordUnsolved(question.id);
    }
  }, []);

  useEffect(() => {
    if (savedValue === value) {
      examContext.recordSaved(question.id);
    } else {
      examContext.recordUnsaved(question.id);
    }
  }, [value !== savedValue]);

  const moveCursor = useRef(null);

  useLayoutEffect(() => {
    if (moveCursor.current !== null) {
      const { target, pos } = moveCursor.current;
      target.selectionStart = pos;
      target.selectionEnd = pos;
      moveCursor.current = null;
    }
  }, [moveCursor.current]);

  let contents;
  if (question.type === "multiple_choice") {
    contents = (
      <div style={{ marginBottom: 10 }}>
        {question.options.map((option) => (
          <Form.Check
            key={option.text}
            custom
            checked={value === option.text}
            name={question.id}
            type="radio"
            label={<span dangerouslySetInnerHTML={{ __html: option.html }} />}
            value={option.text}
            id={`${question.id}|${option.text}`}
            onChange={(e) => {
              setValue(e.target.value);
            }}
          />
        ))}
      </div>
    );
  } else if (question.type === "select_all") {
    contents = (
      <div style={{ marginBottom: 10 }}>
        {question.options.map((option) => (
          <Form.Check
            key={option.text}
            custom
            checked={value.includes(option.text)}
            name={question.id}
            type="checkbox"
            label={<span dangerouslySetInnerHTML={{ __html: option.html }} />}
            value={option.text}
            id={`${question.id}|${option.text}`}
            onChange={(e) => {
              setValue(
                (Array.isArray(value) ? value : [])
                  .filter((x) => x !== e.target.value)
                  .concat(e.target.checked ? [e.target.value] : [])
              );
            }}
          />
        ))}
      </div>
    );
  } else if (question.type === "short_answer") {
    contents = (
      <InputGroup className="mb-3">
        <FormControl
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
          }}
        />
      </InputGroup>
    );
  } else if (question.type === "short_code_answer") {
    contents = (
      <InputGroup className="mb-3">
        <FormControl
          style={{ fontFamily: "monospace" }}
          value={value}
          onChange={(e) => {
            setValue(e.target.value);
          }}
        />
      </InputGroup>
    );
  } else if (question.type === "long_answer") {
    contents = (
      <InputGroup className="mb-3">
        <FormControl
          as="textarea"
          value={value}
          rows={question.options}
          onChange={(e) => {
            setValue(e.target.value);
          }}
        />
      </InputGroup>
    );
  } else if (question.type === "long_code_answer") {
    const tabHandler = (e) => {
      if (e.keyCode === 9) {
        e.preventDefault();
        const { target } = e;
        const start = target.selectionStart;
        const end = target.selectionEnd;
        setValue(`${value.substring(0, start)}\t${value.substring(end)}`);
        moveCursor.current = { target, pos: target.selectionStart + 1 };
      }
    };
    contents = (
      <InputGroup className="mb-3">
        <FormControl
          as="textarea"
          style={{
            fontFamily: '"Lucida Console", Monaco, monospace',
            tabSize: 4,
          }}
          value={value}
          onKeyDown={tabHandler}
          rows={question.options}
          onChange={(e) => {
            setValue(e.target.value);
          }}
        />
      </InputGroup>
    );
  }

  const submitValue = async (val, savedVal) => {
    if (val === savedVal || saving) {
      return;
    }
    setSaving(true);
    try {
      const ret = await post("submit_question", {
        id: question.id,
        value: val,
        sentTime: new Date().getTime(),
        token: getToken(),
        exam: examContext.exam,
      });
      setSaving(false);
      if (!ret.ok) {
        setFailText("Server failed to respond, please try again.");
        examContext.onInternetError();
        return;
      }
      try {
        const data = await ret.json();
        if (!data.success) {
          setFailText(
            "Server responded but failed to save, please refresh and try again."
          );
          examContext.onInternetError();
        } else {
          setSavedValue(val);
          setFailText("");
        }
      } catch {
        setFailText("Server returned invalid JSON. Please try again.");
        examContext.onInternetError();
      }
    } catch {
      setSaving(false);
      setFailText("Unable to reach server, your network may have issues.");
      examContext.onInternetError();
    }
  };

  const submit = () => submitValue(value, savedValue);

  const debouncedSubmit = useCallback(debounce(submitValue, 3000), []);
  useEffect(() => {
    debouncedSubmit(value, savedValue);
    // normally cancelled on next rerender, but fires on unmount
    return () => debouncedSubmit(value, savedValue);
  }, [value, savedValue]);

  const starred = examContext.starredQuestions.get(question.id);

  const starColor = starred ? "orange" : "black";
  const starBody = starred ? <>&#9733;</> : <>&#9734;</>;

  const toggleStarred = (e) => {
    e.preventDefault();
    examContext.setStarred(question.id, !starred);
  };

  return (
    <>
      <Form
        onSubmit={(e) => {
          e.preventDefault();
          submit();
        }}
      >
        <Form.Label style={{ width: "100%" }}>
          <Anchor name={number} />
          <h5 style={{ marginTop: 8, marginBottom: 0 }}>
            Q{number}
            {/* eslint-disable-next-line jsx-a11y/anchor-is-valid */}
            <a
              href="#"
              onClick={toggleStarred}
              className="badge badge-light"
              style={{ float: "right", fontSize: "100%", color: starColor }}
            >
              {starBody}
            </a>
          </h5>{" "}
          <Points points={question.points} />
          <div
            style={{ marginTop: 8 }}
            dangerouslySetInnerHTML={{ __html: question.html }}
          />
        </Form.Label>
        {contents}
        <LoadingButton
          loading={saving}
          disabled={saving || value === savedValue}
          onClick={submit}
        >
          {/* eslint-disable-next-line no-nested-ternary */}
          {value === savedValue ? "Saved" : saving ? "Saving..." : "Save"}
        </LoadingButton>
        <FailText text={failText} />
      </Form>
      <br />
    </>
  );
}
