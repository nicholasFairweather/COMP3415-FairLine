import { isValidEmail, isValidPassword } from "../src/utils/validation.js";

test("accepts a valid email", () => {
    expect(isValidEmail("owen@lakeheadu.ca")).toBe(true);
});

test("rejects an invalid email", () => {
    expect(isValidEmail("not-an-email")).toBe(false);
});

test("rejects a password shorter than 8 characters", () => {
    expect(isValidPassword("1234567")).toBe(false);
});

test("accepts a password of 8 characters", () => {
    expect(isValidPassword("12345678")).toBe(true);
});