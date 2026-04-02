import * as crypto from "crypto"
export const handler = async (event, context, callback) => {
    const request = event.Records[0].cf.request;
    if (request.method === "POST") {
        let hash
        if (request.body && request.body.data) {
            const data = request.body.encoding === "base64" ? Buffer.from(request.body.data, 'base64') : request.body.data
            hash = crypto.createHash('sha256').update(data).digest('hex');
        } else {
            hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        }
        request.headers['x-amz-content-sha256'] = [{ key: 'x-amz-content-sha256', value: hash }];
    }
    return callback(null, request);
};