import { createContext, useContext, useState, type ReactNode } from 'react';
import { useForm, FormProvider, useFormContext, useFieldArray, useWatch } from 'react-hook-form';
import { useMutation, useQuery } from '@tanstack/react-query';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Plus, Trash2 } from 'lucide-react';
import {
  bodySchema,
  formValue,
  defaults,
  displaySchema,
  normalize,
  validator,
  type JsonSchema,
} from '../api/contract';
import { command, queryClient, resourceOptions, type Page } from '../api/client';
import type { paths } from '../api/schema';
import { label } from '../lib/format';
import { Dialog } from './ui/dialog';
import { Button } from './ui/button';
import { Copyable, ErrorState, RecordDetails, type Row } from './data';
const ReferenceContext = createContext<string | undefined>(undefined);
export type Action = {
  title: string;
  path: string;
  contract: keyof paths;
  description?: string;
  initial?: Row;
  hidden?: string[];
  disabled?: boolean;
  success?: (data: Row) => void;
};
function Fields({
  schema,
  prefix = '',
  hidden = [],
}: {
  schema: JsonSchema;
  prefix?: string;
  hidden?: string[];
}) {
  return (
    <>
      {Object.entries(displaySchema(schema).properties ?? {})
        .filter(([key]) => !hidden.includes(key))
        .map(([key, s]) => (
          <Field
            key={key}
            name={prefix ? `${prefix}.${key}` : key}
            schema={s}
            required={schema.required?.includes(key)}
          />
        ))}
    </>
  );
}
function ArrayField({ name, schema }: { name: string; schema: JsonSchema }) {
  const { control } = useFormContext();
  const { fields, append, remove } = useFieldArray({ control, name });
  const s = displaySchema(schema.items ?? {});
  return (
    <fieldset className="array-field">
      <legend>{label(name.split('.').pop()!)}</legend>
      {fields.map((field, i) => (
        <div className="array-item" key={field.id}>
          {s.type === 'object' ? (
            <Fields schema={s} prefix={`${name}.${i}`} />
          ) : (
            <Field name={`${name}.${i}`} schema={s} required />
          )}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => remove(i)}
            aria-label="Remover item"
          >
            <Trash2 size={14} />
            Remover
          </Button>
        </div>
      ))}
      <Button type="button" variant="outline" size="sm" onClick={() => append(defaults(s))}>
        <Plus size={14} />
        Adicionar {label(name.split('.').pop()!).toLowerCase()}
      </Button>
    </fieldset>
  );
}
function ReferenceField({
  name,
  kind,
  required,
}: {
  name: string;
  kind: 'program_id' | 'campaign_id';
  required?: boolean;
}) {
  const {
    register,
    control,
    formState: { errors },
  } = useFormContext();
  const [offset, setOffset] = useState(0);
  const scopedProgram = useContext(ReferenceContext);
  const chosenProgram = useWatch({
    control,
    name: name.includes('.')
      ? name.slice(0, name.lastIndexOf('.') + 1) + 'program_id'
      : 'program_id',
  });
  const current = useWatch({ control, name });
  const program = chosenProgram || scopedProgram;
  const url =
    kind === 'program_id'
      ? `/v1/programs?limit=25&offset=${offset}`
      : `/v1/programs/${program}/campaigns?limit=25&offset=${offset}`;
  const q = useQuery({
    ...resourceOptions<Page<Row>>(url),
    enabled: kind === 'program_id' || !!program,
  });
  return (
    <div className="form-field">
      <label htmlFor={`field-${name}`}>
        {label(kind)}
        {required ? ' *' : ''}
      </label>
      <select id={`field-${name}`} {...register(name)}>
        <option value="">
          {kind === 'campaign_id' ? 'Sem campanha específica' : 'Selecione um programa'}
        </option>
        {current && !q.data?.items.some((r) => r.id === current) ? (
          <option value={String(current)}>{String(current)}</option>
        ) : null}
        {q.data?.items.map((r) => (
          <option key={String(r.id)} value={String(r.id)}>
            {String(r.name)}
          </option>
        ))}
      </select>
      {q.error ? <ErrorState error={q.error} retry={() => void q.refetch()} /> : null}
      {q.data && q.data.total > 25 ? (
        <div className="toolbar-group">
          <Button
            type="button"
            size="sm"
            variant="ghost"
            disabled={!offset}
            onClick={() => setOffset(offset - 25)}
          >
            Anterior
          </Button>
          <small>
            {offset + 1}–{Math.min(offset + 25, q.data.total)} de {q.data.total}
          </small>
          <Button
            type="button"
            size="sm"
            variant="ghost"
            disabled={offset + 25 >= q.data.total}
            onClick={() => setOffset(offset + 25)}
          >
            Próxima
          </Button>
        </div>
      ) : null}
      {errors[name]?.message ? (
        <small role="alert" className="field-error">
          {String(errors[name]?.message)}
        </small>
      ) : null}
    </div>
  );
}
function MetricsField({ name }: { name: string }) {
  const { control, setValue } = useFormContext();
  const values = useWatch({ control, name }) ?? {};
  const [key, setKey] = useState('');
  return (
    <fieldset className="form-field">
      <legend>Métricas sociais</legend>
      {Object.entries(values).map(([k, v]) => (
        <label className="metric-input" key={k}>
          {k}
          <input
            type="number"
            min="0"
            step="1"
            value={String(v)}
            onChange={(e) => setValue(name, { ...values, [k]: Number(e.target.value) })}
          />
          <Button
            type="button"
            variant="ghost"
            size="sm"
            aria-label={`Remover métrica ${k}`}
            onClick={() => {
              const next = { ...values };
              delete next[k];
              setValue(name, next);
            }}
          >
            <Trash2 size={14} />
          </Button>
        </label>
      ))}
      <div className="toolbar-group">
        <input
          aria-label="Nome da métrica"
          placeholder="Ex.: views, likes, comments"
          value={key}
          onChange={(e) => setKey(e.target.value)}
        />
        <Button
          type="button"
          variant="outline"
          size="sm"
          disabled={!key.trim() || ['__proto__', 'constructor', 'prototype'].includes(key.trim())}
          onClick={() => {
            setValue(name, { ...values, [key.trim()]: 0 });
            setKey('');
          }}
        >
          Adicionar métrica
        </Button>
      </div>
    </fieldset>
  );
}
function Field({
  name,
  schema,
  required,
}: {
  name: string;
  schema: JsonSchema;
  required?: boolean;
}) {
  const {
    register,
    formState: { errors },
  } = useFormContext();
  const s = displaySchema(schema);
  const fieldName = name.split('.').pop()!;
  const id = `field-${name}`;
  const err = name
    .split('.')
    .reduce<unknown>((current, key) => (current as Record<string, unknown>)?.[key], errors) as
    { message?: string } | undefined;
  if (fieldName === 'program_id' || fieldName === 'campaign_id')
    return <ReferenceField name={name} kind={fieldName} required={required} />;
  if (fieldName === 'metrics') return <MetricsField name={name} />;
  if (s.type === 'array') return <ArrayField name={name} schema={s} />;
  if (s.type === 'object' && s.properties)
    return (
      <fieldset>
        <legend>{label(fieldName)}</legend>
        <Fields schema={s} prefix={name} />
      </fieldset>
    );
  const options = register(
    name,
    s.type === 'object'
      ? {
          setValueAs: (v: unknown) => {
            if (typeof v !== 'string') return v;
            try {
              return JSON.parse(v);
            } catch {
              return v;
            }
          },
        }
      : {},
  );
  return (
    <div className="form-field">
      <label htmlFor={id}>
        {label(fieldName)}
        {required ? <span aria-hidden="true"> *</span> : null}
      </label>
      {s.enum ? (
        <select id={id} {...options}>
          <option value="">Selecione</option>
          {s.enum.map((v) => (
            <option key={v} value={v}>
              {label(v)} · {v}
            </option>
          ))}
        </select>
      ) : s.type === 'boolean' ? (
        <input id={id} type="checkbox" {...options} />
      ) : s.type === 'object' ? (
        <textarea id={id} rows={3} placeholder='{"views": 100}' {...options} />
      ) : ['content', 'briefing', 'motivation', 'note', 'comment', 'caption'].includes(
          fieldName,
        ) ? (
        <textarea id={id} rows={4} {...options} />
      ) : (
        <input
          id={id}
          type={
            fieldName === 'password'
              ? 'password'
              : s.format === 'date-time'
                ? 'datetime-local'
                : s.format === 'email'
                  ? 'email'
                  : s.type === 'integer'
                    ? 'number'
                    : 'text'
          }
          inputMode={s.pattern ? 'decimal' : undefined}
          min={s.minimum}
          max={s.maximum}
          autoComplete={
            fieldName === 'password' ? 'current-password' : fieldName === 'email' ? 'email' : 'off'
          }
          {...options}
          aria-invalid={!!err}
          aria-describedby={err ? `${id}-error` : undefined}
        />
      )}{' '}
      {s.format === 'date-time' ? <small>Horário local; enviado com fuso à API.</small> : null}
      {['rate', 'base_rate'].includes(fieldName) ? (
        <small>Taxa decimal entre 0 e 1. Exemplo: 0.10 corresponde a 10%.</small>
      ) : null}
      {err?.message ? (
        <small id={`${id}-error`} role="alert" className="field-error">
          {err.message}
        </small>
      ) : null}
    </div>
  );
}
export function ContractForm({
  schema,
  initial,
  hidden = [],
  onSubmit,
  submitLabel,
  pending,
  error,
  errorTitle,
  errorRetry = true,
}: {
  schema: JsonSchema;
  initial?: Row;
  hidden?: string[];
  onSubmit: (data: Row) => void;
  submitLabel: string;
  pending?: boolean;
  error?: unknown;
  errorTitle?: string;
  errorRetry?: boolean;
}) {
  const form = useForm<Row>({
    defaultValues: { ...(defaults(schema) as Row), ...initial },
    mode: 'onBlur',
    resolver: zodResolver(
      z
        .record(z.unknown())
        .transform((values) => {
          try {
            return normalize(values, schema);
          } catch {
            return values;
          }
        })
        .pipe(validator(schema)),
    ),
  });
  return (
    <FormProvider {...form}>
      <form
        className="contract-form"
        noValidate
        onSubmit={form.handleSubmit((values) => {
          form.clearErrors();
          let normalized: unknown;
          try {
            normalized = normalize(values, schema);
          } catch {
            form.setError('root', { message: 'Informe datas e valores válidos.' });
            return;
          }
          const result = validator(schema).safeParse(normalized);
          if (!result.success) {
            result.error.issues.forEach((issue) =>
              form.setError(issue.path.join('.') || 'root', { message: issue.message }),
            );
            return;
          }
          onSubmit(result.data as Row);
        })}
      >
        {schema.properties?.posts ? (
          <div className="form-field">
            <label htmlFor="import-file">Carregar arquivo JSON local (opcional)</label>
            <input
              id="import-file"
              type="file"
              accept=".json,application/json"
              onChange={async (e) => {
                const file = e.target.files?.[0];
                if (!file) return;
                if (file.size > 5_000_000) {
                  form.setError('root', { message: 'Use um arquivo de até 5 MB.' });
                  return;
                }
                try {
                  const value = JSON.parse(await file.text());
                  form.setValue(
                    'posts',
                    formValue(Array.isArray(value) ? value : value.posts, schema.properties!.posts),
                  );
                  form.clearErrors();
                } catch {
                  form.setError('root', { message: 'Não foi possível ler o JSON local.' });
                }
              }}
            />
            <small>Revise os campos abaixo antes de confirmar a importação.</small>
          </div>
        ) : null}
        <Fields schema={schema} hidden={hidden} />
        {form.formState.errors.root ? (
          <p role="alert" className="field-error">
            {form.formState.errors.root.message}
          </p>
        ) : null}
        {error ? (
          <ErrorState
            error={error}
            title={errorTitle}
            retry={
              errorRetry
                ? () => void queryClient.invalidateQueries({ queryKey: ['api'] })
                : undefined
            }
          />
        ) : null}
        <Button type="submit" disabled={pending}>
          {pending ? 'Aguarde…' : submitLabel}
        </Button>
      </form>
    </FormProvider>
  );
}
const ActionContext = createContext<(action: Action) => void>(() => {
  throw new Error('ActionProvider ausente');
});
export function ActionProvider({ children }: { children: ReactNode }) {
  const [action, setAction] = useState<Action | null>(null);
  return (
    <ActionContext.Provider value={setAction}>
      {children}
      {action ? (
        <ActionHost
          key={action.path + action.title}
          action={action}
          close={() => setAction(null)}
        />
      ) : null}
    </ActionContext.Provider>
  );
}
export function ActionButton({ action }: { action: Action }) {
  const show = useContext(ActionContext);
  return (
    <Button variant="outline" size="sm" disabled={action.disabled} onClick={() => show(action)}>
      {action.title}
    </Button>
  );
}
function ActionHost({ action, close }: { action: Action; close: () => void }) {
  const [result, setResult] = useState<Row | null>(null);
  const mutation = useMutation({
    mutationFn: (data: Row) =>
      command<Row>(
        action.path,
        Object.keys(bodySchema(action.contract).properties ?? {}).length ? data : undefined,
      ),
    onSuccess: (data) => {
      setResult(data);
      action.success?.(data);
    },
  });
  return (
    <Dialog
      open
      onOpenChange={(v) => {
        if (!v && !mutation.isPending) close();
      }}
      title={result ? 'Ação concluída' : action.title}
      description={
        action.description ??
        'Confira os dados antes de confirmar. A operação será validada pelo servidor local.'
      }
    >
      {result ? (
        <>
          <div role="status" className="success-message">
            Solicitação registrada com sucesso.
          </div>
          {typeof result.token === 'string' ? (
            <div className="notice">
              <div>
                <strong>Copie o convite agora. Ele só aparece nesta resposta.</strong>
                <Copyable value={`${location.origin}/invite/${result.token}`} />
              </div>
            </div>
          ) : (
            <RecordDetails data={result} />
          )}
          <Button onClick={close}>Concluir</Button>
        </>
      ) : (
        <ReferenceContext.Provider value={action.path.match(/\/programs\/([^/]+)/)?.[1]}>
          <ContractForm
            schema={bodySchema(action.contract)}
            initial={action.initial}
            hidden={action.hidden}
            onSubmit={(data) => mutation.mutate(data)}
            submitLabel={`Confirmar: ${action.title.toLowerCase()}`}
            pending={mutation.isPending}
            error={mutation.error}
          />
        </ReferenceContext.Provider>
      )}
    </Dialog>
  );
}
