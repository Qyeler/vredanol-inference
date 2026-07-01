# UML: Service Flow

This diagram describes the main Vredanol service flow with the frontend already available. It shows authorization, profile usage, barcode recognition, ML image inference, result editing, and analytics.

```mermaid
sequenceDiagram
    actor User as Пользователь
    participant FE as Frontend
    participant API as Backend API
    participant Auth as Auth Service
    participant Profile as Profile Service
    participant Barcode as Barcode Service
    participant Redis as Redis Queue
    participant Worker as Inference Worker
    participant ONNX as ONNX Runtime
    participant Analytics as Analytics Service

    User->>FE: Open app
    FE->>API: Request session
    API->>Auth: Validate token / credentials
    Auth-->>API: Auth result

    alt Authorized
        API->>Profile: Load user profile
        Profile-->>API: Profile, history, settings
        API-->>FE: User workspace

        User->>FE: Upload photo or scan barcode
        FE->>API: Send image/barcode payload

        alt Barcode provided
            API->>Barcode: Find product by barcode
            Barcode-->>API: Product card or not found

            alt Product found
                API->>Analytics: Track barcode recognition
                API-->>FE: Product card
            else Product not found
                API->>Redis: Enqueue inference.classify
                Redis-->>Worker: Deliver classification task
                Worker->>Worker: Decode base64 image
                Worker->>Worker: Resize, crop, normalize
                Worker->>ONNX: Run ConvNeXt Tiny model
                ONNX-->>Worker: Logits
                Worker->>Worker: Softmax and top-k sorting
                Worker-->>API: Top-k predictions
                API->>Analytics: Track ML fallback
                API-->>FE: Recognition variants
            end

        else Image only
            API->>Redis: Enqueue inference.classify
            Redis-->>Worker: Deliver classification task
            Worker->>Worker: Decode base64 image
            Worker->>Worker: Resize, crop, normalize
            Worker->>ONNX: Run ConvNeXt Tiny model
            ONNX-->>Worker: Logits
            Worker->>Worker: Softmax and top-k sorting
            Worker-->>API: Top-k predictions
            API->>Analytics: Track image recognition
            API-->>FE: Recognition variants
        end

        User->>FE: Confirm or edit product data
        FE->>API: Save confirmed/edited card
        API->>Profile: Save to user history/profile
        API->>Analytics: Track correction and final label
        API-->>FE: Saved result

    else Unauthorized
        API-->>FE: Authorization required
        FE-->>User: Show login screen
    end
```

## Key Service Responsibilities

- `Frontend` handles user interaction: login, upload, barcode scan, confirmation, and editing.
- `Backend API` coordinates product scenarios and chooses barcode or ML recognition flow.
- `Auth Service` protects personal profile and history.
- `Profile Service` stores user-specific data, recognition history, and edited cards.
- `Barcode Service` resolves known products by barcode.
- `Inference Worker` runs image classification in the background through Celery.
- `ONNX Runtime` executes the ConvNeXt Tiny model.
- `Analytics Service` collects recognition events, corrections, activity, and quality signals.
