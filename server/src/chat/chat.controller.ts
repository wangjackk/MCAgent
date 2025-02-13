import { Controller, Post, Body } from '@nestjs/common';
import { MemberService } from './member.service';

@Controller('chat')
export class ChatController {
  constructor(private readonly memberService: MemberService) {}

  @Post('signup')
  async handleSignup(@Body() data: any): Promise<any> {
    console.log('signup:', data);

    // 创建或更新新成员
    const success = await this.memberService.createMember(
      data.member_id,
      data.member_name,
      data.description,
    );

    // 返回结果给客户端
    if (success) {
      return {
        status: 201,
        message: 'Member created successfully',
        data: { member_id: data.member_id, member_name: data.member_name },
      };
    }
    return {
      status: 400,
      message: 'Member creation failed, member already exists',
    };
  }
}
