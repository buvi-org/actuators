import fs from "node:fs/promises";
import { defaults, studyPayload, profileDXF } from "../src/lamination-math.js";
await fs.mkdir("public/design", { recursive: true });
await fs.writeFile(
  "public/design/lamination-study.json",
  JSON.stringify(studyPayload(defaults), null, 2) + "\n",
);
await fs.writeFile(
  "public/design/provisional-lamination-mm.dxf",
  profileDXF(defaults),
);
console.log("Exported provisional lamination profile and default stack study.");
