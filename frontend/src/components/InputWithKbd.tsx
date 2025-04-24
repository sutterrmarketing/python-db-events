'use client';

import { useState } from "react";
import { Input, InputGroup, Kbd } from "@chakra-ui/react";
import { LuSearch } from "react-icons/lu";

interface InputWithKbdProps {
  onSearch?: (term: string) => void;
}

const InputWithKbd = ({ onSearch }: InputWithKbdProps) => {
  const [value, setValue] = useState("");

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const term = e.target.value;
    setValue(term);
    onSearch?.(term); // Trigger callback to parent
  };

  return (
    <InputGroup
      flex="1"
      startElement={<LuSearch />}
    >
      <Input
        placeholder="Search Clients"
        value={value}
        onChange={handleChange}
      />
    </InputGroup>
  );
};

export default InputWithKbd;
