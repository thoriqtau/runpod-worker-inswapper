# Swap all the faces in the target image with the source face

## Request

If you have a target image that has more than one face, and you
want to swap the source image into all of the faces in the target
image, you can set `target_index` to a value of `-1` (this is
the default if you do not provide a `target_index` in your payload).

```json
{
  "input": {
    "source_image": "base64 encoded source image content",
    "target_image": "base64 encoded target image content",
    "target_index": -1
  }
}
```

## Response

## RUN

```json
{
  "id": "83bbc301-5dcd-4236-9293-a65cdd681858",
  "status": "IN_QUEUE"
}
```

## RUNSYNC


```json
{
  "delayTime": 20275,
  "executionTime": 43997,
  "id": "sync-a3b54383-e671-4e24-a7bd-c5fec16fda3b",
  "output": {
    "status": "ok",
    "image": "base64 encoded output image"
  },
  "status": "COMPLETED"
}
```
