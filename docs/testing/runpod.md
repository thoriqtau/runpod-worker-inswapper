## Testing your RunPod Endpoint

### Configure your RunPod Credentials

1. Change directory to the `tests/runpod` directory
```bash
cd tests/runpod
```
2. Copy the `.env.example` file to `.env`:
```bash
cd tests
cp .env.example .env
```
3. Edit the `.env` file and add your RunPod API key to
`RUNPOD_API_KEY` and your RunPod Endpoint ID to
`RUNPOD_ENDPOINT_ID`.
4. Run one of the scripts, for example:
```bash
python3 all_1_source_into_all_1_target.py
```
5. This will display the HTTP status code and the filename
   of the output image, for example:
```
Status code: 200
Saving image: 792a7e9f-9c36-4d35-b408-0d45d8e2bbcb.jpg
```

You can then open the output image (in this case
`792a7e9f-9c36-4d35-b408-0d45d8e2bbcb.jpg`) to view the
results of the face swap.
