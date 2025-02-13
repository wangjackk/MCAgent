import { Injectable } from '@nestjs/common';
import Redis from 'ioredis';

@Injectable()
export class MessageStatusService {
  private redisClient: Redis;

  constructor() {
    this.redisClient = new Redis({
      host: 'localhost', // Redis server host
      port: 6379, // Redis server port
      // password: 'your_redis_password', // if Redis is secured with password
    });

    this.redisClient.on('connect', () => {
      console.log('redis connected');
    });
  }

  // 初始化消息状态
  async initMessageStatus(
    message_id: string,
    members: string[],
  ): Promise<void> {
    const status = {};
    members.forEach((member) => {
      status[member] = 0; // 直接使用 member_id 作为键
    });

    // 使用HMSET存储所有接收者的初始状态
    await this.redisClient.hset(`message_status:${message_id}`, status);
    // 设置消息状态的过期时间为1小时（3600秒）
    await this.redisClient.expire(`message_status:${message_id}`, 3600);
  }

  // 更新单个接收者的消息状态为 1 (received)
  async updateMessageStatus(
    message_id: string,
    member_id: string,
    status: 0 | 1,
  ): Promise<void> {
    await this.redisClient.hset(
      `message_status:${message_id}`,
      member_id,
      status,
    );
  }

  async getMessageStatus(message_id: string): Promise<Record<string, 0 | 1>> {
    const status = await this.redisClient.hgetall(
      `message_status:${message_id}`,
    );

    // 将字符串 "0" 或 "1" 转换为数字 0 或 1
    const convertedStatus: Record<string, 0 | 1> = {};
    for (const member in status) {
      convertedStatus[member] = status[member] === '1' ? 1 : 0;
    }

    return convertedStatus;
  }

  async waitForAllReceived(
    message_id: string,
    members: string[],
    timeout: number = 3000, // 超时时间
  ): Promise<string[]> {
    return new Promise((resolve) => {
      const startTime = Date.now();
      const checkStatus = async () => {
        const status = await this.getMessageStatus(message_id);
        const notReceivedMembers = members.filter(
          (member) => status[member] !== 1,
        );

        // 如果所有接收者都确认收到了消息
        if (notReceivedMembers.length === 0) {
          await this.deleteMessageStatus(message_id);
          resolve([]);
        } else {
          const elapsedTime = Date.now() - startTime;
          if (elapsedTime >= timeout) {
            await this.deleteMessageStatus(message_id);
            resolve(notReceivedMembers); // 返回未收到消息的成员列表
          } else {
            // 如果没有超时则继续检查
            setTimeout(checkStatus, 1000);
          }
        }
      };

      // 初始调用
      checkStatus();
    });
  }

  // 删除消息状态
  async deleteMessageStatus(message_id: string): Promise<void> {
    await this.redisClient.del(`message_status:${message_id}`);
  }
}
