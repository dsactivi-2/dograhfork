import { describe, expect, it } from "vitest";

import {
    getBooleanSchema,
    getNumberSchema,
    isFieldVisibleForModel,
    type SchemaProperty,
} from "./serviceConfigurationSchema";

const novaListenFlag: SchemaProperty = {
    type: "boolean",
    hidden_for_models: ["flux-general-en", "flux-general-multi"],
};

describe("isFieldVisibleForModel", () => {
    it("shows Nova Listen flags for nova-3 and custom Nova models", () => {
        expect(isFieldVisibleForModel(novaListenFlag, "nova-3-general")).toBe(true);
        expect(isFieldVisibleForModel(novaListenFlag, "nova-3-medical")).toBe(true);
        expect(isFieldVisibleForModel(novaListenFlag, "nova-2")).toBe(true);
    });

    it("hides Nova Listen flags for Flux models (unsupported params → WS 1006)", () => {
        expect(isFieldVisibleForModel(novaListenFlag, "flux-general-en")).toBe(false);
        expect(isFieldVisibleForModel(novaListenFlag, "flux-general-multi")).toBe(false);
    });

    it("keeps fields without hide/show lists visible", () => {
        expect(isFieldVisibleForModel({ type: "boolean" }, "flux-general-en")).toBe(true);
        expect(isFieldVisibleForModel({ type: "string" }, undefined)).toBe(true);
    });
});

describe("schema type helpers", () => {
    it("treats integer endpointing as a number input", () => {
        expect(getNumberSchema({ type: "integer", minimum: 10, maximum: 5000 })?.type).toBe(
            "integer",
        );
        expect(getNumberSchema({ anyOf: [{ type: "integer" }] })?.type).toBe("integer");
    });

    it("detects boolean switches including anyOf wrappers", () => {
        expect(getBooleanSchema({ type: "boolean" })?.type).toBe("boolean");
        expect(getBooleanSchema({ anyOf: [{ type: "boolean" }, { type: "null" }] })?.type).toBe(
            "boolean",
        );
    });
});
