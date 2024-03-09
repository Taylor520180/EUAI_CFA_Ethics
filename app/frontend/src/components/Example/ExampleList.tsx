import { Example } from "./Example";

import styles from "./Example.module.css";

const DEFAULT_EXAMPLES: string[] = [
    "Explain to me what Soft Dollar Arrangement is?",
    "What is Mosaic Theory in the investment industry?",
    "Give me an example of material non-public information."
];

const GPT4V_EXAMPLES: string[] = [
    "Explain to me what Soft Dollar Arrangement is?",
    "What is Mosaic Theory in the investment industry?",
    "Give me an example of material non-public information."
];

interface Props {
    onExampleClicked: (value: string) => void;
    useGPT4V?: boolean;
}

export const ExampleList = ({ onExampleClicked, useGPT4V }: Props) => {
    return (
        <ul className={styles.examplesNavList}>
            {(useGPT4V ? GPT4V_EXAMPLES : DEFAULT_EXAMPLES).map((question, i) => (
                <li key={i}>
                    <Example text={question} value={question} onClick={onExampleClicked} />
                </li>
            ))}
        </ul>
    );
};
