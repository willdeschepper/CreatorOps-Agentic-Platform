import raw from './contract.json';
import { z } from 'zod';
export type JsonSchema = {
  $ref?: string;
  type?: string;
  title?: string;
  format?: string;
  enum?: string[];
  const?: unknown;
  anyOf?: JsonSchema[];
  properties?: Record<string, JsonSchema>;
  items?: JsonSchema;
  required?: string[];
  default?: unknown;
  minimum?: number;
  maximum?: number;
  exclusiveMinimum?: number;
  minLength?: number;
  maxLength?: number;
  minItems?: number;
  maxItems?: number;
  pattern?: string;
  additionalProperties?: JsonSchema | boolean;
};
export type Operation = {
  parameters?: { name: string; in: string; schema: JsonSchema }[];
  requestBody?: { content: Record<string, { schema: JsonSchema }> };
};
const contract = raw as unknown as {
  schemas: Record<string, JsonSchema>;
  paths: Record<string, Record<string, Operation>>;
};
export function resolve(schema: JsonSchema): JsonSchema {
  return schema.$ref ? resolve(contract.schemas[schema.$ref.split('/').pop()!] ?? {}) : schema;
}
export function displaySchema(schema: JsonSchema): JsonSchema {
  const value = resolve(schema);
  return value.anyOf
    ? displaySchema(
        value.anyOf.find((v) => v.type !== 'null' && v.type !== 'number') ?? value.anyOf[0],
      )
    : value;
}
export function operation(path: string, method = 'get') {
  return contract.paths[path]?.[method];
}
export function bodySchema(path: string) {
  return resolve(
    operation(path, 'post')?.requestBody?.content['application/json']?.schema ?? {
      type: 'object',
      properties: {},
    },
  );
}
export function defaults(schema: JsonSchema): unknown {
  const s = resolve(schema);
  if (s.default !== undefined) return s.default;
  const d = displaySchema(s);
  if (d.type === 'object')
    return Object.fromEntries(Object.entries(d.properties ?? {}).map(([k, v]) => [k, defaults(v)]));
  if (d.type === 'array') return [];
  if (d.type === 'boolean') return false;
  return '';
}
export function validator(schema: JsonSchema): z.ZodTypeAny {
  const s = resolve(schema);
  if (s.anyOf) {
    const options = s.anyOf.map(validator);
    return z.union(options as [z.ZodTypeAny, z.ZodTypeAny, ...z.ZodTypeAny[]]);
  }
  if (s.enum) return z.enum(s.enum as [string, ...string[]]);
  if (s.const !== undefined) return z.literal(s.const as string);
  if (s.type === 'null') return z.null();
  if (s.type === 'boolean') return z.boolean();
  if (s.type === 'integer' || s.type === 'number') {
    let n = z.number();
    if (s.type === 'integer') n = n.int();
    if (s.minimum !== undefined) n = n.min(s.minimum);
    if (s.maximum !== undefined) n = n.max(s.maximum);
    return n;
  }
  if (s.type === 'array') {
    let a = z.array(validator(s.items ?? {}));
    if (s.minItems) a = a.min(s.minItems);
    if (s.maxItems) a = a.max(s.maxItems);
    return a;
  }
  if (s.type === 'object') {
    if (!s.properties)
      return z.record(
        typeof s.additionalProperties === 'object'
          ? validator(s.additionalProperties)
          : z.unknown(),
      );
    return z.object(
      Object.fromEntries(
        Object.entries(s.properties).map(([k, v]) => [
          k,
          s.required?.includes(k) ? validator(v) : validator(v).optional(),
        ]),
      ),
    );
  }
  let str = z.string();
  if (s.minLength) str = str.min(s.minLength, `Use pelo menos ${s.minLength} caracteres.`);
  if (s.maxLength) str = str.max(s.maxLength);
  if (s.pattern) str = str.regex(new RegExp(s.pattern), 'Formato inválido.');
  if (s.format === 'uuid') str = str.uuid('Informe um identificador válido.');
  if (s.format === 'email') str = str.email('Informe um e-mail válido.');
  if (s.format === 'date-time')
    str = str.datetime({ offset: true, message: 'Informe data e horário válidos.' });
  if (s.format === 'uri') str = str.url();
  return str;
}
export function normalize(value: unknown, schema: JsonSchema): unknown {
  const s = resolve(schema),
    d = displaySchema(s);
  if (value === '' || value === undefined) {
    if (s.anyOf?.some((v) => v.type === 'null')) return null;
    if (s.default !== undefined) return s.default;
    return value;
  }
  if (d.type === 'object' && value && typeof value === 'object')
    return Object.fromEntries(
      Object.entries(value)
        .map(([k, v]) => [k, normalize(v, d.properties?.[k] ?? {})])
        .filter(([k, v]) => v !== '' || d.required?.includes(k as string)),
    );
  if (d.type === 'array' && Array.isArray(value))
    return value.map((v) => normalize(v, d.items ?? {}));
  if (d.type === 'integer') return Number(value);
  if (d.format === 'date-time' && typeof value === 'string') return new Date(value).toISOString();
  return value;
}

/** Prepare imported timestamps for native local datetime controls without losing the instant. */
export function formValue(value: unknown, schema: JsonSchema): unknown {
  const s = displaySchema(schema);
  if (s.format === 'date-time' && typeof value === 'string') {
    const time = new Date(value);
    if (!Number.isNaN(time.getTime())) {
      return new Date(time.getTime() - time.getTimezoneOffset() * 60_000)
        .toISOString()
        .slice(0, -1);
    }
  }
  if (s.type === 'array' && Array.isArray(value))
    return value.map((item) => formValue(item, s.items ?? {}));
  if (s.type === 'object' && value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, formValue(item, s.properties?.[key] ?? {})]),
    );
  }
  return value;
}
