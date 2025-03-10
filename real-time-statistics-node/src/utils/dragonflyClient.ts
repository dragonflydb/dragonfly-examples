import { Redis as Dragonfly } from 'ioredis';

// Create and export the Dragonfly client.
// Make sure a Dragonfly server is running locally on port 6379 (default).
const dragonfly = new Dragonfly({
    host: 'localhost',
    port: 6379,
});

export default dragonfly;
