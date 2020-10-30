import React, { useState } from "react";
import { Button, FormControl, InputGroup } from "react-bootstrap";

import { Secret, Token } from "fernet";
import FailText from "./FailText";

export default function PasswordDecryptor({ encryptedExam, onDecrypt }) {
  const [password, setPassword] = useState("");

  const [failText, setFailText] = useState("");

  const decrypt = () => {
    try {
      const secret = new Secret(password.trim());
      const token = new Token({
        secret,
        token: encryptedExam,
        ttl: 0,
      });
      onDecrypt(JSON.parse(token.decode()));
    } catch (e) {
      console.error(e);
      setFailText("Wrong password! (or other decryption error)");
    }
  };

  return (
    <>
      <InputGroup className="mb-3">
        <FormControl
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </InputGroup>
      <Button variant="primary" type="submit" onClick={decrypt}>
        Decrypt
      </Button>
      <FailText text={failText} />
    </>
  );
}
