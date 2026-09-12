import fs from 'node:fs/promises';
import openapiTS, { astToString } from 'openapi-typescript';
const response = await fetch('http://localhost:8000/openapi.json');
if (!response.ok) throw new Error(`OpenAPI local indisponível: ${response.status}`);
const schema = await response.json();
await fs.writeFile(
  new URL('../openapi.json', import.meta.url),
  JSON.stringify(schema, null, 2) + '\n',
);
await fs.writeFile(
  new URL('../src/api/schema.d.ts', import.meta.url),
  astToString(await openapiTS(schema)),
);
// Only the local API's schemas and operation metadata are bundled for form validation.
await fs.writeFile(
  new URL('../src/api/contract.json', import.meta.url),
  JSON.stringify({ schemas: schema.components.schemas, paths: schema.paths }),
);
