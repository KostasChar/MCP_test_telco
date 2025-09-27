
---

## **Step-by-step explanation**

1. **Client sends JSON request**  
   - Example: `{ "device": { "phoneNumber": "+123456789" }, "qosProfile": "voice", "duration": 3600 }`

2. **MCP server parses JSON into Pydantic object**  
   - Ensures all fields exist and types are correct.

3. **Validation happens**  
   - Checks required fields and custom rules (`DeviceInput.check_one_identifier`).

4. **Pydantic object converted to JSON + merged with template**  
   - `model_dump(exclude_unset=True)` removes unset optional fields.  
   - Resulting dictionary is merged into the JSON template.

5. **HTTP request sent to Session Service**  
   - MCP server uses `requests.post` to create a QoD session.

6. **Session Service responds with JSON**  
   - Example: `{ "sessionId": "abc123", "qosStatus": "active" }`

7. **MCP server parses JSON into Pydantic response object**  
   - Converts JSON into `QoDSessionMinimalResponse` or `QoDSessionFullResponse`.

8. **Return typed Pydantic object to client/internal call**  
   - Downstream code can safely access `response.sessionId` and `response.qosStatus` without manual JSON parsing.

