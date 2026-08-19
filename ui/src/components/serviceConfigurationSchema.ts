export interface SchemaProperty {
    type?: string;
    default?: string | number | boolean;
    anyOf?: SchemaProperty[];
    minimum?: number;
    maximum?: number;
    enum?: string[];
    examples?: string[];
    model_options?: Record<string, string[]>;
    allow_custom_input?: boolean;
    $ref?: string;
    description?: string;
    format?: string;
    multiline?: boolean;
    docs_url?: string;
    visible_for_models?: string[];
    hidden_for_models?: string[];
}

export function getSchemaDropdownOptions(
    schema: SchemaProperty | undefined,
    modelValue?: string,
): string[] | undefined {
    let dropdownOptions = schema?.enum || schema?.examples;

    if (schema?.model_options && modelValue && schema.model_options[modelValue]) {
        dropdownOptions = schema.model_options[modelValue];
    }

    return dropdownOptions;
}

export function getNumberSchema(schema: SchemaProperty | undefined): SchemaProperty | undefined {
    if (schema?.type === "number" || schema?.type === "integer") return schema;
    return schema?.anyOf?.find(
        option => option.type === "number" || option.type === "integer",
    );
}

export function getBooleanSchema(schema: SchemaProperty | undefined): SchemaProperty | undefined {
    if (schema?.type === "boolean") return schema;
    return schema?.anyOf?.find(option => option.type === "boolean");
}

export function isFieldVisibleForModel(
    schema: SchemaProperty | undefined,
    modelValue?: string,
): boolean {
    const hidden = schema?.hidden_for_models;
    if (hidden && hidden.length > 0 && modelValue && hidden.includes(modelValue)) {
        return false;
    }
    const allowed = schema?.visible_for_models;
    if (!allowed || allowed.length === 0) return true;
    if (!modelValue) return true;
    return allowed.includes(modelValue);
}
