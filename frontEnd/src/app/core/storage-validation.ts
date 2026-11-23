export function objectValue(value: unknown, keys?: readonly string[]): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) {
    throw new Error('Expected an object.');
  }
  const record = value as Record<string, unknown>;
  if (keys && (Object.keys(record).length !== keys.length || keys.some(key => !Object.hasOwn(record, key)))) {
    throw new Error('Unexpected or missing fields.');
  }
  return record;
}

export function textValue(value: unknown, maximum: number, allowEmpty = true): string {
  if (typeof value !== 'string' || value.length > maximum || (!allowEmpty && !value.trim())) {
    throw new Error('Invalid text.');
  }
  return value;
}

export function booleanValue(value: unknown): boolean {
  if (typeof value !== 'boolean') throw new Error('Expected a boolean.');
  return value;
}

export function optionValue<const T extends string>(value: unknown, options: readonly T[]): T {
  if (typeof value !== 'string' || !options.includes(value as T)) throw new Error('Invalid option.');
  return value as T;
}

export function integerValue(value: unknown, minimum = 0): number {
  if (typeof value !== 'number' || !Number.isSafeInteger(value) || value < minimum) {
    throw new Error('Invalid integer.');
  }
  return value;
}

export function uniqueValues<T>(values: T[]): T[] {
  if (new Set(values).size !== values.length) throw new Error('Duplicate identifiers.');
  return values;
}

/** Browser reads can default invalid fields; explicit imports still use strict parsers. */
export function recoverValue<T>(value: unknown, parse: (value: unknown) => T, fallback: T): T {
  try {
    return parse(value);
  } catch {
    return fallback;
  }
}
