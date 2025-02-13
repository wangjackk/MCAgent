import { Injectable } from '@nestjs/common';
import { Socket } from 'socket.io';
import { Cron } from '@nestjs/schedule';

@Injectable()
export class OnlineMembersService {
  private onlineMembers: Map<string, Socket> = new Map();

  async updateOnlineMember(memberId: string, socket: Socket): Promise<void> {
    console.log('updateOnlineMember:', memberId);
    // console.log('updateOnlineMember:', socket);
    this.onlineMembers.set(memberId, socket);
    console.log('onlineMembers:', this.onlineMembers.keys());
  }

  async getSocketByMemberId(memberId: string): Promise<Socket | undefined> {
    return this.onlineMembers.get(memberId);
  }

  async getOnlineMembers(): Promise<any> {
    return Array.from(this.onlineMembers.keys());
  }

  async removeOnlineMember(memberId: string): Promise<void> {
    // console.log('remove');
    this.onlineMembers.delete(memberId);
  }

  async removeOnlineMemberBySocket(socket: Socket): Promise<void> {
    const member = await this.findOnlineMemberBySocket(socket);
    if (member) {
      await this.removeOnlineMember(member);
    }
  }

  async findOnlineMemberBySocket(socket: Socket): Promise<string | undefined> {
    for (const [memberId, value] of this.onlineMembers) {
      if (value === socket) {
        return memberId;
      }
    }
    return undefined;
  }
  //每10秒检查一次
  // @Cron('*/10 * * * * *')
  async checkOnlineMembers() {
    // console.log('checkOnlineMembers');
    const onlineMembers = await this.getOnlineMembers();
    for (const member of onlineMembers) {
      const socket = await this.getSocketByMemberId(member);
      // 检查socket是否在线
      if (!socket.connected) {
        await this.removeOnlineMember(member);
      }
    }
  }
}
