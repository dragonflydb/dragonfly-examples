import { Redis as Dragonfly } from 'ioredis';

export class DragonflyPublisher {
    private pub: Dragonfly;
    private channel: string;

    constructor(channel: string) {
        const dragonfly = new Dragonfly({
            host: process.env.DRAGONFLY_HOST || 'localhost',
            port: parseInt(process.env.DRAGONFLY_PORT || '6380', 10),
        });
        this.pub = dragonfly;
        this.channel = channel;
    }

    publish(message: string) {
        this.pub.publish(this.channel, message);
    }

    close() { this.pub.quit(); }
}
